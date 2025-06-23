import { renderHook, act } from '@testing-library/react';
import { useFinancialCalculations } from '../useFinancialCalculations';
import { calculationService } from '../../services/calculationService';
import { ModelComponent } from '../../utils/calculationEngine';

// Mock the calculation service
jest.mock('../../services/calculationService');
const mockCalculationService = calculationService as jest.Mocked<typeof calculationService>;

describe('useFinancialCalculations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCalculationService.healthCheck.mockResolvedValue(false); // Default to offline
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useFinancialCalculations(null));

    expect(result.current.calculations).toEqual({});
    expect(result.current.summary).toEqual({
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
    expect(result.current.isCalculating).toBe(false);
    expect(result.current.isBackendConnected).toBe(false);
  });

  it('should update component properties', () => {
    const model = {
      components: [
        {
          id: 'test-1',
          type: 'revenue',
          properties: { amount: 1000 },
          position: { x: 0, y: 0 },
          x: 0,
          y: 0
        }
      ]
    };

    const { result } = renderHook(() => useFinancialCalculations(model));

    act(() => {
      result.current.updateComponent('test-1', { amount: 2000 });
    });

    // Check that the component was updated
    expect(result.current.exportModel().components[0].properties.amount).toBe(2000);
  });

  it('should export and import model data correctly', () => {
    const model = {
      components: [
        {
          id: 'test-1',
          type: 'revenue',
          properties: { amount: 1000 },
          position: { x: 0, y: 0 },
          x: 0,
          y: 0
        }
      ]
    };

    const { result } = renderHook(() => useFinancialCalculations(model));

    // Export model
    const exportedModel = result.current.exportModel();
    expect(exportedModel.components).toHaveLength(1);
    expect(exportedModel.metadata).toBeDefined();
    expect(exportedModel.metadata?.version).toBe('1.0');

    // Clear and import model
    act(() => {
      result.current.importModel(exportedModel);
    });

    expect(result.current.exportModel().components).toHaveLength(1);
  });

  it('should generate scenarios based on current summary', async () => {
    const model = {
      components: [
        {
          id: 'test-1',
          type: 'revenue',
          properties: { amount: 1000 },
          position: { x: 0, y: 0 },
          x: 0,
          y: 0
        }
      ]
    };

    const { result } = renderHook(() => useFinancialCalculations(model));

    await act(async () => {
      await result.current.generateScenarios();
    });

    expect(result.current.scenarios).toBeDefined();
    expect(result.current.scenarios?.baseCase).toBeDefined();
    expect(result.current.scenarios?.optimistic).toBeDefined();
    expect(result.current.scenarios?.pessimistic).toBeDefined();
  });

  it('should handle invalid model data import gracefully', () => {
    const { result } = renderHook(() => useFinancialCalculations(null));

    expect(() => {
      act(() => {
        result.current.importModel({ components: null as unknown as ModelComponent[], connections: [] });
      });
    }).toThrow('Invalid model data: components array is required');
  });

  it('should filter invalid components during import', () => {
    const { result } = renderHook(() => useFinancialCalculations(null));

    const invalidModel = {
      components: [
        { id: 'valid', type: 'revenue', properties: {} },
        { id: '', type: 'revenue', properties: {} }, // Invalid - empty id
        { type: 'revenue', properties: {} }, // Invalid - missing id
      ],
      connections: []
    };

    act(() => {
      result.current.importModel(invalidModel);
    });

    // Should only have the valid component
    expect(result.current.exportModel().components).toHaveLength(1);
    expect(result.current.exportModel().components[0].id).toBe('valid');
  });

  it('should try backend calculation when connected', async () => {
    mockCalculationService.healthCheck.mockResolvedValue(true);
    mockCalculationService.calculateROI.mockResolvedValue({
      detailed_calculations: { 
        'test-1': { 
          value: 1000, 
          type: 'currency', 
          confidence: 0.8, 
          formatted: '$1,000', 
          dependencies: [] 
        } 
      },
      total_annual_gain: 1000,
      roi_percentage: 100,
      payback_period_months: 12,
      npv: 1000,
      irr: 0.25,
      confidence_score: 0.8
    });
    mockCalculationService.convertToSummary.mockReturnValue({
      totalRevenue: 1000,
      totalCosts: 0,
      netValue: 1000,
      netBenefit: 1000,
      roi: 100,
      confidence: 0.8,
      paybackPeriod: 1,
      npv: 1000,
      irr: 100
    });

    const model = {
      components: [
        {
          id: '1',
          name: 'Revenue Component',
          type: 'revenue' as const,
          category: 'input',
          properties: {
            value: 100000,
            type: 'currency' as const
          },
          position: { x: 100, y: 100 }
        }
      ]
    };

    const { result } = renderHook(() => useFinancialCalculations(model));

    // Wait for backend check and calculations
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(result.current.isBackendConnected).toBe(true);
    expect(mockCalculationService.calculateROI).toHaveBeenCalled();
  });
});
