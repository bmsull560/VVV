import { DiscoveryResponse, ValueDriverPillar } from '../services/b2bValueApi';
import { DiscoveryData } from '../services/modelBuilderApi';

/**
 * Converts a DiscoveryResponse from the API to the DiscoveryData format expected by components
 */
export function adaptDiscoveryResponseToData(response: DiscoveryResponse): DiscoveryData {
  return {
    valueDrivers: response.value_drivers.map(pillar => ({
      category: pillar.pillar,
      description: `Value drivers for ${pillar.pillar.toLowerCase()}`,
      metrics: pillar.tier_3_metrics.map(metric => ({
        name: metric.name,
        description: metric.description,
        value: metric.suggested_value,
        unit: metric.unit,
        confidence: metric.confidence_level === 'high' ? 0.9 : 
                  metric.confidence_level === 'medium' ? 0.6 : 0.3
      }))
    })),
    personas: response.personas.map(persona => ({
      id: persona.name.toLowerCase().replace(/\s+/g, '-'),
      name: persona.name,
      description: persona.description,
      priorities: persona.priorities,
      concerns: persona.concerns,
      role: persona.name // Using name as role since it's a simple mapping
    })),
    suggestedMetrics: response.suggested_metrics.map(metric => ({
      id: metric.name,
      name: metric.name,
      description: metric.description,
      unit: metric.unit,
      suggestedValue: metric.suggested_value,
      confidence: metric.confidence_level === 'high' ? 0.9 : 
                metric.confidence_level === 'medium' ? 0.6 : 0.3
    })),
    projectInsights: {
      industryContext: response.project_insights.industry_context,
      complexityAssessment: response.project_insights.complexity_assessment,
      recommendedApproach: response.project_insights.recommended_approach
    }
  };
}

/**
 * Creates a mapping between the original value driver structure and the adapted one
 */
export function createValueDriverMapping(response: DiscoveryResponse): Record<string, string> {
  const mapping: Record<string, string> = {};
  
  response.value_drivers.forEach(pillar => {
    pillar.tier_3_metrics.forEach(metric => {
      mapping[metric.name] = `${pillar.pillar} - ${metric.name}`;
    });
  });
  
  return mapping;
}
