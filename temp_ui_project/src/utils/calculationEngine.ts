/**
 * Financial Calculation Engine (TypeScript)
 * Handles various financial metrics and formula evaluation for visual model builder
 */

export interface ComponentProperties {
  [key: string]: any;
}

export interface ModelComponent {
  id: string;
  type: string;
  properties: ComponentProperties;
  position?: { x: number; y: number };
  connections?: string[];
}

export interface CalculationResult {
  value: number;
  formatted: string;
  confidence: number;
  dependencies: string[];
  type?: 'currency' | 'percentage' | 'number';
}

export interface CalculationSummary {
  totalRevenue: number;
  totalCosts: number;
  netValue: number;
  netBenefit: number;
  roi: number;
  confidence: number;
  paybackPeriod?: number;
  npv?: number;
  irr?: number;
}

export class FinancialCalculationEngine {
  private components: Map<string, ModelComponent> = new Map();
  private dependencies: Map<string, Set<string>> = new Map();
  private calculationCache: Map<string, CalculationResult> = new Map();

  /**
   * Register a component with its properties
   */
  registerComponent(component: ModelComponent): void {
    this.components.set(component.id, component);
    this.invalidateCache(component.id);
    this.updateDependencies();
  }

  /**
   * Update component properties
   */
  updateComponent(componentId: string, properties: ComponentProperties): void {
    const component = this.components.get(componentId);
    if (component) {
      component.properties = { ...component.properties, ...properties };
      this.invalidateCache(componentId);
      this.propagateChanges(componentId);
    }
  }

  /**
   * Calculate value for a specific component
   */
  calculateComponent(componentId: string): CalculationResult {
    const component = this.components.get(componentId);
    if (!component) {
      return { value: 0, formatted: '$0', confidence: 0, dependencies: [] };
    }

    // Check cache first
    if (this.calculationCache.has(componentId)) {
      return this.calculationCache.get(componentId)!;
    }

    let result: CalculationResult = { value: 0, formatted: '$0', confidence: 1, dependencies: [] };

    try {
      switch (component.type) {
        case 'revenue-stream':
          result = this.calculateRevenueStream(component);
          break;
        case 'cost-center':
          result = this.calculateCostCenter(component);
          break;
        case 'roi-calculator':
          result = this.calculateROI(component);
          break;
        case 'npv-calculator':
          result = this.calculateNPV(component);
          break;
        case 'payback-calculator':
          result = this.calculatePayback(component);
          break;
        case 'sensitivity-analysis':
          result = this.calculateSensitivity(component);
          break;
        case 'variable':
          result = this.calculateVariable(component);
          break;
        case 'formula':
          result = this.calculateFormula(component);
          break;
        default:
          result = { value: component.properties.value || 0, formatted: this.formatCurrency(component.properties.value || 0), confidence: 0.8, dependencies: [] };
      }
    } catch (error) {
      console.error(`Calculation error for component ${componentId}:`, error);
      result = { value: 0, formatted: 'Error', confidence: 0, dependencies: [] };
    }

    // Cache the result
    this.calculationCache.set(componentId, result);
    return result;
  }

  /**
   * Calculate revenue stream
   */
  private calculateRevenueStream(component: ModelComponent): CalculationResult {
    const { unitPrice = 0, quantity = 0, growthRate = 0, periods = 12 } = component.properties;
    
    let totalRevenue = 0;
    let currentRevenue = unitPrice * quantity;
    
    for (let i = 0; i < periods; i++) {
      totalRevenue += currentRevenue;
      currentRevenue *= (1 + growthRate / 100);
    }

    return {
      value: totalRevenue,
      formatted: this.formatCurrency(totalRevenue),
      confidence: 0.9,
      dependencies: [],
      type: 'currency'
    };
  }

  /**
   * Calculate cost center
   */
  private calculateCostCenter(component: ModelComponent): CalculationResult {
    const { monthlyCost = 0, periods = 12, escalationRate = 0 } = component.properties;
    
    let totalCost = 0;
    let currentCost = monthlyCost;
    
    for (let i = 0; i < periods; i++) {
      totalCost += currentCost;
      currentCost *= (1 + escalationRate / 100);
    }

    return {
      value: totalCost,
      formatted: this.formatCurrency(totalCost),
      confidence: 0.9,
      dependencies: [],
      type: 'currency'
    };
  }

  /**
   * Calculate ROI
   */
  private calculateROI(component: ModelComponent): CalculationResult {
    const { investment = 0, annualBenefit = 0, periods = 3 } = component.properties;
    
    const totalBenefit = annualBenefit * periods;
    const roi = investment > 0 ? ((totalBenefit - investment) / investment) * 100 : 0;

    return {
      value: roi,
      formatted: this.formatPercentage(roi),
      confidence: 0.85,
      dependencies: [],
      type: 'percentage'
    };
  }

  /**
   * Calculate NPV
   */
  private calculateNPV(component: ModelComponent): CalculationResult {
    const { cashFlows = [], discountRate = 0.1 } = component.properties;
    
    let npv = 0;
    cashFlows.forEach((cashFlow: number, index: number) => {
      npv += cashFlow / Math.pow(1 + discountRate, index);
    });

    return {
      value: npv,
      formatted: this.formatCurrency(npv),
      confidence: 0.8,
      dependencies: [],
      type: 'currency'
    };
  }

  /**
   * Calculate payback period
   */
  private calculatePayback(component: ModelComponent): CalculationResult {
    const { investment = 0, annualCashFlow = 0 } = component.properties;
    
    const paybackPeriod = annualCashFlow > 0 ? investment / annualCashFlow : 0;

    return {
      value: paybackPeriod,
      formatted: this.formatPeriod(paybackPeriod * 12), // Convert to months
      confidence: 0.9,
      dependencies: [],
      type: 'number'
    };
  }

  /**
   * Calculate sensitivity analysis
   */
  private calculateSensitivity(component: ModelComponent): CalculationResult {
    const { baseCase = 0, scenarios = [] } = component.properties;
    
    const variance = scenarios.reduce((acc: number, scenario: number) => {
      return acc + Math.pow(scenario - baseCase, 2);
    }, 0) / scenarios.length;
    
    const standardDeviation = Math.sqrt(variance);
    const sensitivity = baseCase > 0 ? (standardDeviation / baseCase) * 100 : 0;

    return {
      value: sensitivity,
      formatted: this.formatPercentage(sensitivity),
      confidence: 0.7,
      dependencies: [],
      type: 'percentage'
    };
  }

  /**
   * Calculate variable
   */
  private calculateVariable(component: ModelComponent): CalculationResult {
    const { value = 0, formula } = component.properties;
    
    if (formula) {
      return this.evaluateFormula(formula);
    }

    return {
      value: value,
      formatted: this.formatCurrency(value),
      confidence: 1,
      dependencies: [],
      type: 'currency'
    };
  }

  /**
   * Calculate formula
   */
  private calculateFormula(component: ModelComponent): CalculationResult {
    const { formula = '' } = component.properties;
    return this.evaluateFormula(formula);
  }

  /**
   * Evaluate formula with component references
   */
  private evaluateFormula(formula: string): CalculationResult {
    try {
      // Replace component references with their calculated values
      let evaluatedFormula = formula;
      const componentRefs = formula.match(/\$([a-zA-Z0-9_]+)/g) || [];
      
      componentRefs.forEach(ref => {
        const componentId = ref.substring(1);
        const result = this.calculateComponent(componentId);
        evaluatedFormula = evaluatedFormula.replace(ref, result.value.toString());
      });

      // Evaluate the mathematical expression
      const result = this.safeEvaluate(evaluatedFormula);
      
      return {
        value: result,
        formatted: this.formatCurrency(result),
        confidence: 0.8,
        dependencies: componentRefs.map(ref => ref.substring(1)),
        type: 'currency'
      };
    } catch (error) {
      console.error('Formula evaluation error:', error);
      return { value: 0, formatted: 'Error', confidence: 0, dependencies: [] };
    }
  }

  /**
   * Safe mathematical expression evaluation
   */
  private safeEvaluate(expression: string): number {
    // Basic mathematical operations only
    const sanitized = expression.replace(/[^0-9+\-*/().\s]/g, '');
    try {
      return Function(`"use strict"; return (${sanitized})`)();
    } catch {
      return 0;
    }
  }

  /**
   * Get all calculations
   */
  getAllCalculations(): Record<string, CalculationResult> {
    const results: Record<string, CalculationResult> = {};
    
    this.components.forEach((component, id) => {
      results[id] = this.calculateComponent(id);
    });

    return results;
  }

  /**
   * Invalidate cache for component and dependents
   */
  private invalidateCache(componentId: string): void {
    this.calculationCache.delete(componentId);
    
    // Invalidate dependents
    this.dependencies.forEach((deps, id) => {
      if (deps.has(componentId)) {
        this.invalidateCache(id);
      }
    });
  }

  /**
   * Propagate changes to dependent components
   */
  private propagateChanges(componentId: string): void {
    this.dependencies.forEach((deps, id) => {
      if (deps.has(componentId)) {
        this.invalidateCache(id);
      }
    });
  }

  /**
   * Update dependency graph
   */
  private updateDependencies(): void {
    this.dependencies.clear();
    
    this.components.forEach((component, id) => {
      const deps = new Set<string>();
      
      if (component.properties.formula) {
        const refs = component.properties.formula.match(/\$([a-zA-Z0-9_]+)/g) || [];
        refs.forEach((ref: string) => deps.add(ref.substring(1)));
      }
      
      this.dependencies.set(id, deps);
    });
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.calculationCache.clear();
  }

  /**
   * Format currency values
   */
  formatCurrency(value: number, currency: string = 'USD'): string {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });

    if (Math.abs(value) >= 1000000) {
      return formatter.format(value / 1000000) + 'M';
    } else if (Math.abs(value) >= 1000) {
      return formatter.format(value / 1000) + 'K';
    }
    
    return formatter.format(value);
  }

  /**
   * Format percentage values
   */
  formatPercentage(value: number, decimals: number = 1): string {
    return `${value.toFixed(decimals)}%`;
  }

  /**
   * Format time periods
   */
  formatPeriod(months: number): string {
    if (months < 1) {
      return `${Math.round(months * 30)} days`;
    } else if (months < 12) {
      return `${Math.round(months)} months`;
    } else {
      const years = Math.floor(months / 12);
      const remainingMonths = Math.round(months % 12);
      return remainingMonths > 0 ? `${years}y ${remainingMonths}m` : `${years} years`;
    }
  }

  /**
   * Calculate all metrics and return summary
   */
  calculateAll(inputs: Record<string, any>): { calculations: Record<string, CalculationResult>; summary: CalculationSummary } {
    const calculations: Record<string, CalculationResult> = {};
    
    // Register components from inputs
    Object.entries(inputs).forEach(([id, data]) => {
      if (data && typeof data === 'object') {
        this.registerComponent({
          id,
          type: data.type || 'unknown',
          properties: data
        });
      }
    });

    // Calculate all registered components
    for (const [id, component] of this.components.entries()) {
      try {
        const result = this.calculateComponent(id);
        if (result) {
          calculations[id] = result;
        }
      } catch (error) {
        console.error(`Error calculating component ${id}:`, error);
      }
    }

    // Generate summary
    const summary = this.generateSummary(calculations);
    
    return { calculations, summary };
  }

  /**
   * Generate summary from calculations
   */
  private generateSummary(calculations: Record<string, CalculationResult>): CalculationSummary {
    let totalRevenue = 0;
    let totalCosts = 0;
    let totalConfidence = 0;
    let componentCount = 0;

    // Aggregate values by component type
    for (const [id, result] of Object.entries(calculations)) {
      const component = this.components.get(id);
      if (!component) continue;

      componentCount++;
      totalConfidence += result.confidence;

      switch (component.type) {
        case 'revenue-stream':
        case 'revenue':
          totalRevenue += result.value;
          break;
        case 'cost-center':
        case 'cost':
          totalCosts += result.value;
          break;
      }
    }

    const netValue = totalRevenue - totalCosts;
    const roi = totalCosts > 0 ? ((netValue / totalCosts) * 100) : 0;
    const confidence = componentCount > 0 ? totalConfidence / componentCount : 0.5;

    return {
      totalRevenue,
      totalCosts,
      netValue,
      netBenefit: netValue, // Add netBenefit to summary
      roi,
      confidence,
      paybackPeriod: netValue > 0 ? totalCosts / (netValue / 12) : 0,
      npv: netValue, // Simplified NPV calculation
      irr: roi // Simplified IRR as ROI percentage
    };
  }
}

// Utility functions for common financial calculations
export class FinancialUtils {
  /**
   * Calculate compound annual growth rate (CAGR)
   */
  static calculateCAGR(beginningValue: number, endingValue: number, periods: number): number {
    if (beginningValue <= 0 || periods <= 0) return 0;
    return (Math.pow(endingValue / beginningValue, 1 / periods) - 1) * 100;
  }

  /**
   * Calculate present value
   */
  static calculatePV(futureValue: number, rate: number, periods: number): number {
    return futureValue / Math.pow(1 + rate, periods);
  }

  /**
   * Calculate future value
   */
  static calculateFV(presentValue: number, rate: number, periods: number): number {
    return presentValue * Math.pow(1 + rate, periods);
  }

  /**
   * Calculate internal rate of return (IRR) using Newton-Raphson method
   */
  static calculateIRR(cashFlows: number[], guess: number = 0.1): number {
    const MAX_ITERATIONS = 100;
    const TOLERANCE = 1e-6;
    
    let rate = guess;
    
    for (let i = 0; i < MAX_ITERATIONS; i++) {
      const npv = cashFlows.reduce((sum, cf, period) => {
        return sum + cf / Math.pow(1 + rate, period);
      }, 0);
      
      const derivativeNPV = cashFlows.reduce((sum, cf, period) => {
        return sum - (period * cf) / Math.pow(1 + rate, period + 1);
      }, 0);
      
      if (Math.abs(derivativeNPV) < TOLERANCE) break;
      
      const newRate = rate - npv / derivativeNPV;
      
      if (Math.abs(newRate - rate) < TOLERANCE) {
        return newRate * 100; // Return as percentage
      }
      
      rate = newRate;
    }
    
    return rate * 100; // Return as percentage
  }
}

// Create singleton instance
export const calculationEngine = new FinancialCalculationEngine();
