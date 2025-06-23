import { useState, useCallback, useEffect } from 'react';
import { calculationEngine, CalculationResult, CalculationSummary } from '../utils/calculationEngine';
import { calculationService } from '../services/calculationService';

interface ModelComponent {
  id: string;
  type: string;
  properties: Record<string, unknown>;
  position?: { x: number; y: number };
}

interface ModelData {
  components: ModelComponent[];
  connections: Array<{ from: string; to: string }>;
  metadata?: Record<string, unknown>;
}

interface UseFinancialCalculationsReturn {
  calculations: Record<string, CalculationResult>;
  summary: CalculationSummary;
  isCalculating: boolean;
  isBackendConnected: boolean;
  recalculate: () => void;
  updateComponent: (componentId: string, properties: Record<string, unknown>) => void;
  getFormattedValue: (componentId: string) => string;
  getConfidence: (componentId: string) => number;
  exportModel: () => ModelData;
  importModel: (modelData: ModelData) => void;
  scenarios: ScenarioAnalysis | null;
  isGenerating: boolean;
  generateScenarios: () => void;
}

interface ScenarioAnalysis {
  baseCase: CalculationSummary;
  optimistic: CalculationSummary;
  pessimistic: CalculationSummary;
}

/**
 * Custom hook for managing financial calculations
 */
export const useFinancialCalculations = (
  model: { components: ModelComponent[] } | null
): UseFinancialCalculationsReturn => {
  const [components, setComponents] = useState<ModelComponent[]>(model?.components || []);
  const [calculations, setCalculations] = useState<Record<string, CalculationResult>>({});
  const [summary, setSummary] = useState<CalculationSummary>({
    totalRevenue: 0,
    totalCosts: 0,
    netValue: 0,
    netBenefit: 0,
    roi: 0,
    confidence: 0.5,
    paybackPeriod: 0,
    npv: 0,
    irr: 0
  });
  const [isCalculating, setIsCalculating] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState(false);

  // Check backend connectivity on mount
  useEffect(() => {
    const checkBackend = async () => {
      const connected = await calculationService.healthCheck();
      setIsBackendConnected(connected);
    };
    checkBackend();
  }, []);

  const performCalculations = useCallback(async () => {
    setIsCalculating(true);
    
    try {
      // Convert components to calculation format
      const calculationInputs = components.reduce((acc, component) => {
        if (component.properties && Object.keys(component.properties).length > 0) {
          acc[component.id] = {
            type: component.type,
            ...component.properties
          };
        }
        return acc;
      }, {} as Record<string, unknown>);

      // Try backend calculation first if connected
      if (isBackendConnected && Object.keys(calculationInputs).length > 0) {
        try {
          const backendResponse = await calculationService.calculateROI(calculationInputs);
          const summary = calculationService.convertToSummary(backendResponse);
          
          setCalculations(backendResponse.detailed_calculations);
          setSummary(summary);
          return;
        } catch (error) {
          console.warn('Backend calculation failed, falling back to frontend:', error);
          setIsBackendConnected(false);
        }
      }

      // Fallback to frontend calculation
      const results = calculationEngine.calculateAll(calculationInputs);
      setCalculations(results.calculations);
      setSummary(results.summary);
    } catch (error) {
      console.error('Calculation error:', error);
      setCalculations({});
      setSummary({
        totalRevenue: 0,
        totalCosts: 0,
        netValue: 0,
        netBenefit: 0,
        roi: 0,
        confidence: 0.5,
        paybackPeriod: 0,
        npv: 0,
        irr: 0
      });
    } finally {
      setIsCalculating(false);
    }
  }, [components, isBackendConnected]);

  const updateComponent = useCallback((componentId: string, properties: Record<string, unknown>) => {
    setComponents(prev => prev.map(comp => 
      comp.id === componentId 
        ? { ...comp, properties: { ...comp.properties, ...properties } }
        : comp
    ));
  }, []);

  const getFormattedValue = useCallback((componentId: string): string => {
    const result = calculations[componentId];
    if (!result) return '0';
    
    if (typeof result.value === 'number') {
      if (result.type === 'currency') {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(result.value);
      } else if (result.type === 'percentage') {
        return `${(result.value * 100).toFixed(2)}%`;
      }
      return result.value.toLocaleString();
    }
    
    return String(result.value);
  }, [calculations]);

  const getConfidence = useCallback((componentId: string): number => {
    const result = calculations[componentId];
    return result?.confidence ?? 0.5;
  }, [calculations]);

  const exportModel = useCallback((): ModelData => {
    return {
      components,
      connections: [], // TODO: Add connection tracking
      metadata: {
        exportDate: new Date().toISOString(),
        version: '1.0',
        summary: {
          totalComponents: components.length,
          ...summary
        }
      }
    };
  }, [components, summary]);

  const importModel = useCallback((modelData: ModelData) => {
    if (!modelData.components || !Array.isArray(modelData.components)) {
      throw new Error('Invalid model data: components array is required');
    }

    // Validate component structure
    const validComponents = modelData.components.filter(component => 
      component.id && 
      component.type && 
      typeof component.properties === 'object'
    );

    if (validComponents.length !== modelData.components.length) {
      console.warn('Some components were filtered out due to invalid structure');
    }

    setComponents(validComponents);
    
    // Trigger recalculation after import
    setTimeout(() => {
      void performCalculations();
    }, 100);
  }, [performCalculations]);

  // Trigger calculations when components change
  useEffect(() => {
    if (components.length > 0) {
      void performCalculations();
    }
  }, [components, performCalculations]);

  // Initialize calculation engine with model components
  useEffect(() => {
    if (model?.components) {
      // Clear existing components
      calculationEngine.clearCache();

      // Register all components
      model.components.forEach(component => {
        calculationEngine.registerComponent(component);
      });

      // Trigger recalculation
      performCalculations();
    }
  }, [model?.components]);

  // Scenario analysis state and functions
  const [scenarios, setScenarios] = useState<ScenarioAnalysis | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateScenarios = useCallback(async () => {
    setIsGenerating(true);
    
    try {
      // Use current calculations as base case for scenario analysis
      const newScenarios: ScenarioAnalysis = {
        baseCase: summary,
        optimistic: {
          ...summary,
          totalRevenue: summary.totalRevenue * 1.2,
          netValue: summary.netValue * 1.15,
          roi: summary.roi * 1.15
        },
        pessimistic: {
          ...summary,
          totalRevenue: summary.totalRevenue * 0.8,
          netValue: summary.netValue * 0.85,
          roi: summary.roi * 0.85
        }
      };

      setScenarios(newScenarios);
    } catch (error) {
      console.error('Scenario generation error:', error);
    } finally {
      setIsGenerating(false);
    }
  }, [summary]);

  return {
    calculations,
    summary,
    isCalculating,
    isBackendConnected,
    recalculate: performCalculations,
    updateComponent,
    getFormattedValue,
    getConfidence,
    exportModel,
    importModel,
    scenarios,
    isGenerating,
    generateScenarios
  };
};
