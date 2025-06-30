"""
Shared validation utilities for agent input validation.

This module provides common validation functions that can be used across
different agents to ensure consistent input validation and error handling.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime, date

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class ValidationResult:
    """Represents the result of a validation operation."""
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors if errors is not None else []

    def __bool__(self):
        return self.is_valid

    def __repr__(self):
        if self.is_valid:
            return "<ValidationResult: Valid>"
        else:
            return f"<ValidationResult: Invalid, Errors: {self.errors}>"

class ValidationType(Enum):
    """Standard validation types."""
    REQUIRED = "required"
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    FORMAT_CHECK = "format_check"
    ENUM_CHECK = "enum_check"
    CUSTOM = "custom"

# =============================================================================
# BASIC TYPE VALIDATION
# =============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that all required fields are present and not empty."""
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Field '{field}' cannot be null")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
    
    return errors

def validate_field_types(data: Dict[str, Any], field_types: Dict[str, str]) -> List[str]:
    """Validate field types against expected types."""
    errors = []
    
    type_mapping = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict
    }
    
    for field, expected_type in field_types.items():
        if field not in data:
            continue
            
        value = data[field]
        expected_python_type = type_mapping.get(expected_type)
        
        if expected_python_type and not isinstance(value, expected_python_type) and value is not None:
            errors.append(f"Field '{field}' must be of type {expected_type}")
    
    return errors

def validate_number_ranges(data: Dict[str, Any], constraints: Dict[str, Dict[str, float]]) -> List[str]:
    """Validate numeric fields against min/max constraints."""
    errors = []
    
    for field, constraint in constraints.items():
        if field not in data:
            continue
            
        value = data[field]
        if not isinstance(value, (int, float)):
            continue
            
        if 'min' in constraint and value < constraint['min']:
            errors.append(f"Field '{field}' must be at least {constraint['min']}")
        
        if 'max' in constraint and value > constraint['max']:
            errors.append(f"Field '{field}' must be at most {constraint['max']}")
    
    return errors

def validate_enum_values(data: Dict[str, Any], enum_constraints: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """Validate enum/choice fields against allowed values."""
    errors = []
    
    for field, constraint in enum_constraints.items():
        if field not in data:
            continue
            
        value = data[field]
        allowed_values = constraint.get('enum', [])
        
        if value not in allowed_values:
            errors.append(f"Field '{field}' must be one of: {', '.join(allowed_values)}")
    
    return errors

# =============================================================================
# BUSINESS LOGIC VALIDATION
# =============================================================================

def validate_project_name(name: str, existing_projects: List[str] = None) -> List[str]:
    """Validate project name format and uniqueness."""
    errors = []
    
    if not name or not name.strip():
        errors.append("Project name is required")
        return errors
    
    name = name.strip()
    
    # Length validation
    if len(name) < 3:
        errors.append("Project name must be at least 3 characters long")
    elif len(name) > 100:
        errors.append("Project name must be at most 100 characters long")
    
    # Format validation
    if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', name):
        errors.append("Project name can only contain letters, numbers, spaces, hyphens, underscores, and periods")
    
    # Uniqueness validation
    if existing_projects and name.lower() in [p.lower() for p in existing_projects]:
        errors.append(f"Project name '{name}' already exists")
    
    return errors

def validate_email_format(email: str) -> List[str]:
    """Validate email address format."""
    errors = []
    
    if not email or not email.strip():
        return errors  # Email might be optional
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email.strip()):
        errors.append("Invalid email format")
    
    return errors

def validate_date_format(date_str: str, field_name: str = "date") -> List[str]:
    """Validate date string format (ISO 8601)."""
    errors = []
    
    if not date_str or not date_str.strip():
        return errors  # Date might be optional
    
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        errors.append(f"Invalid {field_name} format. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
    
    return errors

def validate_percentage(value: float, field_name: str = "percentage") -> List[str]:
    """Validate percentage values (0-100)."""
    errors = []
    
    if not isinstance(value, (int, float)):
        errors.append(f"{field_name} must be a number")
        return errors
    
    if value < 0 or value > 100:
        errors.append(f"{field_name} must be between 0 and 100")
    
    return errors

def validate_currency_amount(amount: float, field_name: str = "amount", min_value: float = 0) -> List[str]:
    """Validate monetary amounts."""
    errors = []
    
    if not isinstance(amount, (int, float)):
        errors.append(f"{field_name} must be a number")
        return errors
    
    if amount < min_value:
        errors.append(f"{field_name} must be at least {min_value}")
    
    # Check for reasonable upper limit to prevent overflow
    if amount > 1e12:  # 1 trillion
        errors.append(f"{field_name} exceeds maximum allowed value")
    
    return errors

# =============================================================================
# ARRAY AND OBJECT VALIDATION
# =============================================================================

def validate_array_structure(data: List[Dict[str, Any]], required_fields: List[str], 
                           array_name: str = "array") -> List[str]:
    """Validate array of objects has required structure."""
    errors = []
    
    if not isinstance(data, list):
        errors.append(f"{array_name} must be an array")
        return errors
    
    if len(data) == 0:
        errors.append(f"{array_name} cannot be empty")
        return errors
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"{array_name}[{i}] must be an object")
            continue
        
        for field in required_fields:
            if field not in item:
                errors.append(f"{array_name}[{i}] missing required field: {field}")
    
    return errors

def validate_stakeholder_structure(stakeholders: List[Dict[str, Any]]) -> List[str]:
    """Validate stakeholder array structure."""
    errors = []
    
    required_fields = ['name', 'role', 'influence_level']
    base_errors = validate_array_structure(stakeholders, required_fields, "stakeholders")
    errors.extend(base_errors)
    
    if base_errors:  # Don't continue if basic structure is invalid
        return errors
    
    valid_roles = ['sponsor', 'owner', 'user', 'approver', 'contributor', 'observer']
    valid_influence_levels = ['high', 'medium', 'low']
    
    for i, stakeholder in enumerate(stakeholders):
        if not isinstance(stakeholder, dict):
            continue
            
        # Validate role
        role = stakeholder.get('role', '').lower()
        if role not in valid_roles:
            errors.append(f"stakeholders[{i}].role must be one of: {', '.join(valid_roles)}")
        
        # Validate influence level
        influence = stakeholder.get('influence_level', '').lower()
        if influence not in valid_influence_levels:
            errors.append(f"stakeholders[{i}].influence_level must be one of: {', '.join(valid_influence_levels)}")
        
        # Validate name
        name = stakeholder.get('name', '').strip()
        if not name:
            errors.append(f"stakeholders[{i}].name cannot be empty")
        elif len(name) < 2:
            errors.append(f"stakeholders[{i}].name must be at least 2 characters")
    
    return errors

# =============================================================================
# BUSINESS DOMAIN VALIDATION
# =============================================================================

def validate_industry_classification(industry: str, department: str = None) -> List[str]:
    """Validate industry and department classification."""
    errors = []
    
    # Standard industry classifications (subset)
    valid_industries = [
        'technology', 'healthcare', 'finance', 'manufacturing', 'retail',
        'education', 'government', 'consulting', 'real_estate', 'energy',
        'transportation', 'telecommunications', 'media', 'agriculture', 'other'
    ]
    
    valid_departments = [
        'it', 'finance', 'hr', 'operations', 'marketing', 'sales',
        'customer_service', 'legal', 'procurement', 'r_and_d', 'executive', 'other'
    ]
    
    if industry and industry.lower() not in valid_industries:
        errors.append(f"Industry must be one of: {', '.join(valid_industries)}")
    
    if department and department.lower() not in valid_departments:
        errors.append(f"Department must be one of: {', '.join(valid_departments)}")
    
    return errors

def validate_business_metrics(metrics: List[Dict[str, Any]]) -> List[str]:
    """Validate business metrics structure."""
    errors = []
    
    required_fields = ['name', 'value']
    base_errors = validate_array_structure(metrics, required_fields, "metrics")
    errors.extend(base_errors)
    
    if base_errors:
        return errors
    
    for i, metric in enumerate(metrics):
        if not isinstance(metric, dict):
            continue
            
        # Validate metric name
        name = metric.get('name', '').strip()
        if not name:
            errors.append(f"metrics[{i}].name cannot be empty")
        
        # Validate metric value
        value = metric.get('value')
        if not isinstance(value, (int, float)):
            errors.append(f"metrics[{i}].value must be a number")
        
        # Validate units if present
        units = metric.get('units', '').strip()
        if units and len(units) > 20:
            errors.append(f"metrics[{i}].units must be 20 characters or less")
    
    return errors

# =============================================================================
# COMPOSITE VALIDATION
# =============================================================================

def validate_comprehensive_input(data: Dict[str, Any], validation_config: Dict[str, Any]) -> List[str]:
    """Perform comprehensive input validation based on configuration."""
    all_errors = []
    
    # Required fields validation
    if 'required_fields' in validation_config:
        all_errors.extend(validate_required_fields(data, validation_config['required_fields']))
    
    # Type validation
    if 'field_types' in validation_config:
        all_errors.extend(validate_field_types(data, validation_config['field_types']))
    
    # Range validation
    if 'field_constraints' in validation_config:
        all_errors.extend(validate_number_ranges(data, validation_config['field_constraints']))
    
    # Enum validation
    if 'enum_constraints' in validation_config:
        all_errors.extend(validate_enum_values(data, validation_config['enum_constraints']))
    
    return all_errors

def format_validation_errors(errors: List[str], context: str = None) -> str:
    """Format validation errors into a readable string."""
    if not errors:
        return ""
    
    header = f"Validation errors{' for ' + context if context else ''}:"
    formatted_errors = [f"  • {error}" for error in errors]
    
    return "\n".join([header] + formatted_errors)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def sanitize_input_string(input_str: str, max_length: int = 1000) -> str:
    """Sanitize input string by removing harmful characters and limiting length."""
    if not isinstance(input_str, str):
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', input_str)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized.strip()

def normalize_enum_value(value: str, valid_values: List[str]) -> Optional[str]:
    """Normalize enum value to match valid options (case-insensitive)."""
    if not isinstance(value, str):
        return None
    
    normalized = value.lower().strip()
    
    for valid_value in valid_values:
        if normalized == valid_value.lower():
            return valid_value
    
    return None

def extract_numeric_value(value: Union[str, int, float]) -> Optional[float]:
    """Extract numeric value from various input types."""
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove common non-numeric characters
        cleaned = re.sub(r'[,$%\s]', '', value.strip())
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None
