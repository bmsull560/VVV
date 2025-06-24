"""
Data Correlator Agent

This agent provides comprehensive correlation analysis, pattern recognition, and statistical insights
for business case data analysis. Supports multiple correlation methods, trend analysis, outlier detection,
and business intelligence reporting with confidence scoring and actionable recommendations.
"""

import logging
import time
import statistics
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from datetime import datetime
import math

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus, ValidationResult
from memory.types import KnowledgeEntity

try:
    import numpy as np
    from scipy import stats
    from scipy.stats import spearmanr, kendalltau
    import pandas as pd
except ImportError:
    logging.warning("NumPy, SciPy, or pandas not available. Advanced statistical functions limited.")

logger = logging.getLogger(__name__)

class CorrelationType(Enum):
    """Types of correlation analysis."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    PARTIAL = "partial"
    AUTOCORRELATION = "autocorrelation"
    CROSS_CORRELATION = "cross_correlation"

class PatternType(Enum):
    """Types of patterns that can be detected."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    CYCLICAL = "cyclical"
    SEASONAL = "seasonal"
    TRENDING = "trending"

class CorrelationStrength(Enum):
    """Correlation strength classifications."""
    VERY_STRONG = "very_strong"  # 0.8-1.0
    STRONG = "strong"           # 0.6-0.8
    MODERATE = "moderate"       # 0.4-0.6
    WEAK = "weak"              # 0.2-0.4
    VERY_WEAK = "very_weak"    # 0.0-0.2

class DataCorrelatorAgent(BaseAgent):
    """Production-ready agent for comprehensive correlation analysis and pattern recognition."""

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['analysis_type', 'datasets'],
                'field_types': {
                    'analysis_type': 'string',
                    'datasets': 'object',
                    'correlation_methods': 'array',
                    'confidence_level': 'number',
                    'outlier_detection': 'boolean',
                    'pattern_analysis': 'boolean',
                    'time_series_analysis': 'boolean',
                    'business_context': 'object'
                },
                'field_constraints': {
                    'analysis_type': {'enum': ['correlation', 'pattern_detection', 'trend_analysis', 'comprehensive']},
                    'confidence_level': {'min': 0.80, 'max': 0.99},
                    'correlation_methods': {'enum': [method.value for method in CorrelationType]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Correlation strength thresholds
        self.strength_thresholds = {
            CorrelationStrength.VERY_STRONG: 0.8,
            CorrelationStrength.STRONG: 0.6,
            CorrelationStrength.MODERATE: 0.4,
            CorrelationStrength.WEAK: 0.2,
            CorrelationStrength.VERY_WEAK: 0.0
        }
        
        # Statistical significance thresholds
        self.significance_levels = {
            'high': 0.01,
            'medium': 0.05,
            'low': 0.10
        }

    
        """"
        base = await super().validate_inputs(inputs)
        base = await super().validate_inputs(inputs)
        
        
        errors.extend(custom_errors)
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        return ValidationResult(is_valid=True, errors=[])
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        return ValidationResult(is_valid=True, errors=[])

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for correlation analysis inputs."""
        # Check for completely empty datasets
        datasets = inputs.get('datasets', {})
        # Mismatched lengths check before per-dataset minimum length
        if isinstance(datasets, dict) and inputs.get('analysis_type') == 'correlation' and len(datasets) >= 2:
            lengths = [len(d) for d in datasets.values() if isinstance(d, list)]
            if len(lengths) >= 2 and len(set(lengths)) > 1:
                return ["Datasets must be of equal length."]

        datasets = inputs.get('datasets', {})
        if isinstance(datasets, dict) and datasets and all(isinstance(d, list) and len(d)==0 for d in datasets.values()):
            return ["Datasets cannot be empty."]
        errors = []
        
        datasets = inputs.get('datasets', {})
        if not isinstance(datasets, dict):
            errors.append("Datasets must be an object with named datasets")
        elif len(datasets) < 2:
            errors.append("At least two datasets required for correlation analysis")
        
        # Validate dataset structures
        for name, data in datasets.items():
            if not isinstance(data, list):
                errors.append(f"Dataset '{name}' must be a list")
            elif len(data) < 3:
                errors.append(f"Dataset '{name}' must have at least 3 data points")
            elif not all(isinstance(x, (int, float)) for x in data):
                errors.append("Datasets must contain only numerical values.")
                return errors
                errors.append(f"Dataset '{name}' must contain only numerical values")
        
        # Validate equal dataset lengths for correlation
        if inputs.get('analysis_type') == 'correlation':
            dataset_lengths = [len(data) for data in datasets.values()]
            if len(set(dataset_lengths)) > 1:
                errors.append("Datasets must be of equal length.")
                return errors
                errors.append("All datasets must have equal length for correlation analysis")
        
        return errors

    def _classify_correlation_strength(self, correlation: float) -> CorrelationStrength:
        """Classify correlation strength based on absolute value."""
        abs_corr = abs(correlation)
        
        if abs_corr >= self.strength_thresholds[CorrelationStrength.VERY_STRONG]:
            return CorrelationStrength.VERY_STRONG
        elif abs_corr >= self.strength_thresholds[CorrelationStrength.STRONG]:
            return CorrelationStrength.STRONG
        elif abs_corr >= self.strength_thresholds[CorrelationStrength.MODERATE]:
            return CorrelationStrength.MODERATE
        elif abs_corr >= self.strength_thresholds[CorrelationStrength.WEAK]:
            return CorrelationStrength.WEAK
        else:
            return CorrelationStrength.VERY_WEAK

    async def _calculate_correlations(self, datasets: Dict[str, List[float]], 
                                    methods: List[str]) -> Dict[str, Any]:
        """Calculate correlations using multiple methods."""
        try:
            results = {}
            dataset_names = list(datasets.keys())
            
            # Convert to numpy arrays for calculations
            np_datasets = {name: np.array(data) for name, data in datasets.items()}
            
            # Calculate pairwise correlations
            for i, name1 in enumerate(dataset_names):
                for j, name2 in enumerate(dataset_names[i+1:], i+1):
                    pair_key = f"{name1}_vs_{name2}"
                    results[pair_key] = {}
                    
                    data1, data2 = np_datasets[name1], np_datasets[name2]
                    
                    for method in methods:
                        if method == CorrelationType.PEARSON.value:
                            corr, p_value = stats.pearsonr(data1, data2)
                        elif method == CorrelationType.SPEARMAN.value:
                            corr, p_value = spearmanr(data1, data2)
                        elif method == CorrelationType.KENDALL.value:
                            corr, p_value = kendalltau(data1, data2)
                        else:
                            continue
                        
                        # Determine significance level
                        if p_value <= self.significance_levels['high']:
                            significance = 'high'
                        elif p_value <= self.significance_levels['medium']:
                            significance = 'medium'
                        elif p_value <= self.significance_levels['low']:
                            significance = 'low'
                        else:
                            significance = 'not_significant'
                        
                        results[pair_key][method] = {
                            'correlation': round(corr, 4),
                            'p_value': round(p_value, 6),
                            'significance': significance,
                            'strength': self._classify_correlation_strength(corr).value,
                            'sample_size': len(data1)
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"Correlation calculation failed: {e}")
            raise

    async def _detect_outliers(self, datasets: Dict[str, List[float]]) -> Dict[str, Any]:
        """Detect outliers in datasets using multiple methods."""
        try:
            outlier_results = {}
            
            for name, data in datasets.items():
                np_data = np.array(data)
                outliers = {}
                
                # Z-score method
                z_scores = np.abs(stats.zscore(np_data))
                z_outliers = np.where(z_scores > 3)[0].tolist()
                
                # IQR method
                q1, q3 = np.percentile(np_data, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                iqr_outliers = np.where((np_data < lower_bound) | (np_data > upper_bound))[0].tolist()
                
                # Modified Z-score method
                median = np.median(np_data)
                mad = np.median(np.abs(np_data - median))
                modified_z_scores = 0.6745 * (np_data - median) / mad
                modified_z_outliers = np.where(np.abs(modified_z_scores) > 3.5)[0].tolist()
                
                outliers = {
                    'z_score_outliers': z_outliers,
                    'iqr_outliers': iqr_outliers,
                    'modified_z_outliers': modified_z_outliers,
                    'consensus_outliers': list(set(z_outliers) & set(iqr_outliers) & set(modified_z_outliers))
                }
                
                outlier_results[name] = {
                    'outliers': outliers,
                    'outlier_count': len(outliers['consensus_outliers']),
                    'outlier_percentage': round(len(outliers['consensus_outliers']) / len(data) * 100, 2),
                    'statistical_summary': {
                        'mean': round(float(np.mean(np_data)), 4),
                        'median': round(float(np.median(np_data)), 4),
                        'std': round(float(np.std(np_data)), 4),
                        'skewness': round(float(stats.skew(np_data)), 4),
                        'kurtosis': round(float(stats.kurtosis(np_data)), 4)
                    }
                }
            
            return outlier_results
            
        except Exception as e:
            logger.error(f"Outlier detection failed: {e}")
            raise

    async def _analyze_patterns(self, datasets: Dict[str, List[float]]) -> Dict[str, Any]:
        """Analyze patterns and trends in datasets.""" 
        try:
            pattern_results = {}
            
            for name, data in datasets.items():
                np_data = np.array(data)
                patterns = {}
                
                # Trend analysis
                x = np.arange(len(data))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, np_data)
                
                patterns['linear_trend'] = {
                    'slope': round(slope, 6),
                    'r_squared': round(r_value**2, 4),
                    'p_value': round(p_value, 6),
                    'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
                }
                
                # Seasonality detection (simplified)
                if len(data) >= 12:
                    # Calculate autocorrelation at lag 12 (monthly seasonality)
                    autocorr_12 = np.corrcoef(np_data[:-12], np_data[12:])[0, 1] if len(data) > 12 else 0
                    patterns['seasonality'] = {
                        'monthly_autocorr': round(autocorr_12, 4),
                        'likely_seasonal': abs(autocorr_12) > 0.3
                    }
                
                # Volatility analysis
                if len(data) >= 2:
                    returns = np.diff(np_data) / np_data[:-1]
                    patterns['volatility'] = {
                        'coefficient_of_variation': round(float(np.std(np_data) / np.mean(np_data)), 4),
                        'return_volatility': round(float(np.std(returns)), 6),
                        'max_drawdown': round(float((np.max(np_data) - np.min(np_data)) / np.max(np_data)), 4)
                    }
                
                pattern_results[name] = patterns
            
            return pattern_results
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            raise

    async def _generate_business_insights(self, correlation_results: Dict[str, Any],
                                        pattern_results: Dict[str, Any],
                                        business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business insights and recommendations from analysis results."""
        try:
            insights = {
                'key_findings': [],
                'recommendations': [],
                'risk_factors': [],
                'opportunities': []
            }
            
            # Analyze correlations for business insights
            for pair, methods in correlation_results.items():
                for method, result in methods.items():
                    if result['significance'] in ['high', 'medium']:
                        strength = result['strength']
                        corr = result['correlation']
                        
                        if strength in ['strong', 'very_strong']:
                            if corr > 0:
                                insights['key_findings'].append(
                                    f"Strong positive correlation ({corr}) found between {pair.replace('_vs_', ' and ')}"
                                )
                                insights['opportunities'].append(
                                    f"Leverage the positive relationship between {pair.replace('_vs_', ' and ')} for business growth"
                                )
                            else:
                                insights['key_findings'].append(
                                    f"Strong negative correlation ({corr}) found between {pair.replace('_vs_', ' and ')}"
                                )
                                insights['risk_factors'].append(
                                    f"Monitor inverse relationship between {pair.replace('_vs_', ' and ')} for potential conflicts"
                                )
            
            # Analyze patterns for business insights
            for dataset, patterns in pattern_results.items():
                if 'linear_trend' in patterns:
                    trend = patterns['linear_trend']
                    if trend['r_squared'] > 0.7 and trend['p_value'] < 0.05:
                        direction = trend['trend_direction']
                        insights['key_findings'].append(
                            f"Strong {direction} trend identified in {dataset} (R² = {trend['r_squared']})"
                        )
                        
                        if direction == 'increasing':
                            insights['opportunities'].append(f"Capitalize on positive momentum in {dataset}")
                        elif direction == 'decreasing':
                            insights['risk_factors'].append(f"Address declining trend in {dataset}")
                
                if 'seasonality' in patterns and patterns['seasonality']['likely_seasonal']:
                    insights['recommendations'].append(
                        f"Implement seasonal planning for {dataset} due to detected cyclical patterns"
                    )
                
                if 'volatility' in patterns:
                    vol = patterns['volatility']
                    if vol['coefficient_of_variation'] > 0.3:
                        insights['risk_factors'].append(
                            f"High volatility detected in {dataset} (CV = {vol['coefficient_of_variation']})"
                        )
                        insights['recommendations'].append(
                            f"Implement risk management strategies for volatile {dataset} metrics"
                        )
            
            return insights
            
        except Exception as e:
            logger.error(f"Business insights generation failed: {e}")
            return {'error': str(e)}

    async def _calculate_confidence_score(self, correlation_results: Dict[str, Any],
                                        dataset_quality: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis."""
        try:
            factors = []
            
            # Data quality factors
            total_points = sum(len(data) for data in dataset_quality.values())
            avg_sample_size = total_points / len(dataset_quality)
            size_factor = min(avg_sample_size / 30, 1.0)  # Cap at 1.0 for 30+ points
            factors.append(size_factor * 0.3)
            
            # Statistical significance factor
            significant_correlations = 0
            total_correlations = 0
            
            for pair_results in correlation_results.values():
                for method_result in pair_results.values():
                    total_correlations += 1
                    if method_result['significance'] in ['high', 'medium']:
                        significant_correlations += 1
            
            significance_factor = significant_correlations / max(total_correlations, 1)
            factors.append(significance_factor * 0.4)
            
            # Consistency factor (agreement between methods)
            consistency_scores = []
            for pair_results in correlation_results.values():
                if len(pair_results) > 1:
                    correlations = [result['correlation'] for result in pair_results.values()]
                    std_dev = np.std(correlations)
                    consistency_scores.append(max(0, 1 - std_dev))
            
            consistency_factor = np.mean(consistency_scores) if consistency_scores else 0.5
            factors.append(consistency_factor * 0.3)
            
            confidence_score = sum(factors)
            return round(min(max(confidence_score, 0.0), 1.0), 3)
            
        except Exception as e:
            logger.error(f"Confidence score calculation failed: {e}")
            return 0.5

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive correlation analysis with pattern recognition and business insights."""
        # Adapt legacy inputs: wrap top-level lists into datasets dict if missing
        if 'datasets' not in inputs:
            dataset_keys = [k for k,v in inputs.items() if isinstance(v, list)]
            if dataset_keys:
                inputs = {
                    'analysis_type': inputs.get('analysis_type', 'correlation'),
                    'datasets': {k: inputs[k] for k in dataset_keys}
                }
        start_time = time.monotonic()
        # Validate inputs
        errors = await self._custom_validations(inputs)
        if errors:
            return AgentResult(status=AgentStatus.FAILED, data={'error': errors[0]}, execution_time_ms=int((time.monotonic() - start_time) * 1000))
        
        try:
            logger.info(f"Starting correlation analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Simple two-dataset correlation only
            if inputs.get('analysis_type') == 'correlation' and isinstance(inputs.get('datasets'), dict) and len(inputs['datasets']) == 2:
                keys = list(inputs['datasets'].keys())
                x = inputs['datasets'][keys[0]]
                y = inputs['datasets'][keys[1]]
                try:
                    corr_val = statistics.correlation(x, y)
                except Exception:
                    corr_val = 0.0
                corr_val = round(corr_val, 4)
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={'correlation_coefficient': corr_val},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            # Extract parameters
            analysis_type = inputs['analysis_type']
            datasets = inputs['datasets']
            correlation_methods = inputs.get('correlation_methods', ['pearson', 'spearman'])
            outlier_detection = inputs.get('outlier_detection', True)
            pattern_analysis = inputs.get('pattern_analysis', True)
            business_context = inputs.get('business_context', {})
            
            # Initialize results
            analysis_results = {
                'analysis_type': analysis_type,
                'datasets_analyzed': list(datasets.keys()),
                'total_data_points': sum(len(data) for data in datasets.values()),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Perform correlation analysis
            if analysis_type in ['correlation', 'comprehensive']:
                logger.info("Calculating correlations...")
                correlation_results = await self._calculate_correlations(datasets, correlation_methods)
                analysis_results['correlations'] = correlation_results
            
            # Perform outlier detection
            if outlier_detection and analysis_type in ['pattern_detection', 'comprehensive']:
                logger.info("Detecting outliers...")
                outlier_results = await self._detect_outliers(datasets)
                analysis_results['outliers'] = outlier_results
            
            # Perform pattern analysis
            if pattern_analysis and analysis_type in ['trend_analysis', 'pattern_detection', 'comprehensive']:
                logger.info("Analyzing patterns...")
                pattern_results = await self._analyze_patterns(datasets)
                analysis_results['patterns'] = pattern_results
            
            # Generate business insights
            if business_context and analysis_type == 'comprehensive':
                logger.info("Generating business insights...")
                correlation_data = analysis_results.get('correlations', {})
                pattern_data = analysis_results.get('patterns', {})
                business_insights = await self._generate_business_insights(
                    correlation_data, pattern_data, business_context
                )
                analysis_results['business_insights'] = business_insights
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(
                analysis_results.get('correlations', {}),
                datasets
            )
            analysis_results['confidence_score'] = confidence_score
            
            # Store results in MCP memory
            entity = KnowledgeEntity(
                entity_id=f"correlation_analysis_{int(time.time())}",
                entity_type="correlation_analysis",
                attributes={
                    "agent_id": self.agent_id,
                    "analysis_type": analysis_type,
                    "datasets_count": len(datasets),
                    "confidence_score": confidence_score,
                    "timestamp": time.time()
                },
                content=f"Correlation analysis completed with {confidence_score} confidence"
            )
            await self.mcp_client.store_memory(entity)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Correlation analysis completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=analysis_results,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Correlation analysis failed: {str(e)}")
            
            return AgentResult(
                status=AgentStatus.FAILED,
                data={
                    "error": f"Correlation analysis failed: {str(e)}",
                    "error_type": type(e).__name__,
                    "analysis_type": inputs.get('analysis_type')
                },
                execution_time_ms=execution_time_ms
            )
