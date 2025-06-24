/**
 * Financial Calculation Engine (TypeScript)
 * Handles various financial metrics and formula evaluation for visual model builder
 */

/**
 * Properties for a revenue stream component.
 */
export interface RevenueStreamProperties {
  unitPrice: number;
  quantity: number;
  growthRate?: number;
  periods?: number;
}

/**
 * Properties for a cost center component.
 */
export interface CostCenterProperties {
  monthlyCost: number;
  periods?: number;
  escalationRate?: number;
}

/**
 * Properties for an ROI calculator component.
 */
export interface ROICalculatorProperties {
  investment: number;
  annualBenefit: number;
  periods?: number;
}

/**
 * Properties for an NPV calculator component.
 */
export interface NPVCalculatorProperties {
  cashFlows: number[];
  discountRate: number;
}

/**
 * Properties for a payback calculator component.
 */
export interface PaybackCalculatorProperties {
  investment: number;
  annualBenefit: number;
}

/**
 * Properties for a sensitivity analysis component.
 */
export interface SensitivityAnalysisProperties {
  baseValue: number;
  rangeMin: number;
  rangeMax: number;
  variableName: string;
}

/**
 * Properties for a variable component.
 */
export interface VariableProperties {
  value: number;
  label?: string;
}

/**
 * Properties for a formula component.
 */
export interface FormulaProperties {
  expression: string;
  variables: Record<string, number>;
}

/**
 * Discriminated union of all component properties.
 */
export type ComponentProperties =
  | RevenueStreamProperties
  | CostCenterProperties
  | ROICalculatorProperties
  | NPVCalculatorProperties
  | PaybackCalculatorProperties
  | SensitivityAnalysisProperties
  | VariableProperties
  | FormulaProperties;


/**
 * Generic model component interface, parameterized by properties type.
 */
export interface ModelComponent<T extends ComponentProperties = ComponentProperties> {
  id: string;
  type: string;
  properties: T;
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
        case 'revenue-stream': {
          // Type guard for RevenueStreamProperties
          result = this.calculateRevenueStream(component as ModelComponent<RevenueStreamProperties>);
          break;
        }
        case 'cost-center': {
          result = this.calculateCostCenter(component as ModelComponent<CostCenterProperties>);
          break;
        }
        case 'roi-calculator': {
          result = this.calculateROI(component as ModelComponent<ROICalculatorProperties>);
          break;
        }
        case 'npv-calculator': {
          result = this.calculateNPV(component as ModelComponent<NPVCalculatorProperties>);
          break;
        }
        case 'payback-calculator': {
          result = this.calculatePayback(component as ModelComponent<PaybackCalculatorProperties>);
          break;
        }
        case 'sensitivity-analysis': {
          result = this.calculateSensitivity(component as ModelComponent<SensitivityAnalysisProperties>);
          break;
        }
        case 'variable': {
          result = this.calculateVariable(component as ModelComponent<VariableProperties>);
          break;
        }
        case 'formula': {
          result = this.calculateFormula(component as ModelComponent<FormulaProperties>);
          break;
        }
        default: {
          // Fallback: if properties has 'value', use it, else 0
          const props = component.properties as Partial<VariableProperties>;
          const value = typeof props.value === 'number' ? props.value : 0;
          result = { value, formatted: this.formatCurrency(value), confidence: 0.8, dependencies: [] };
          break;
        }
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
  /**
   * Calculate revenue stream
   * @param component ModelComponent with RevenueStreamProperties
   */
  private calculateRevenueStream(component: ModelComponent<RevenueStreamProperties>): CalculationResult {
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
   * @param component ModelComponent with CostCenterProperties
   */
  private calculateCostCenter(component: ModelComponent<CostCenterProperties>): CalculationResult {
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
  private calculateROI(component: ModelComponent<ROICalculatorProperties>): CalculationResult {
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
  private calculateNPV(component: ModelComponent<NPVCalculatorProperties>): CalculationResult {
    const { cashFlows, discountRate } = component.properties;
    let npv = 0;
    for (let t = 0; t < cashFlows.length; t++) {
      npv += cashFlows[t] / Math.pow(1 + discountRate / 100, t + 1);
    }
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

  // ...

  /**
   * Calculate all metrics and return summary
   */
  calculateAll(inputs: Record<string, ModelComponent>): { calculations: Record<string, CalculationResult>; summary: CalculationSummary } {
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

  // ...

  /**
   * Generate summary from calculations
   */
  private generateSummary(calculations: Record<string, CalculationResult>): CalculationSummary {
    let totalRevenue: number = 0;
    let totalCosts: number = 0;
    let totalConfidence: number = 0;
    let componentCount: number = 0;

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

    const netValue: number = totalRevenue - totalCosts;
    const roi: number = totalCosts > 0 ? ((netValue / totalCosts) * 100) : 0;
    const confidence: number = componentCount > 0 ? totalConfidence / componentCount : 0.5;

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
  /**
   * Calculate compound annual growth rate (CAGR).
   * @param beginningValue Initial value
   * @param endingValue Final value
   * @param periods Number of periods
   * @returns CAGR as a number
   */
  static calculateCAGR(beginningValue: number, endingValue: number, periods: number): number {
    if (beginningValue <= 0 || periods <= 0) return 0;
    return (Math.pow(endingValue / beginningValue, 1 / periods) - 1) * 100;
  }

  /**
   * Calculate present value
   */
  /**
   * Calculate present value.
   * @param futureValue Future value
   * @param rate Interest rate
   * @param periods Number of periods
   * @returns Present value as a number
   */
  static calculatePV(futureValue: number, rate: number, periods: number): number {
    return futureValue / Math.pow(1 + rate, periods);
  }

  /**
   * Calculate future value
   */
  /**
   * Calculate future value.
   * @param presentValue Present value
   * @param rate Interest rate
   * @param periods Number of periods
   * @returns Future value as a number
   */
  static calculateFV(presentValue: number, rate: number, periods: number): number {
    return presentValue * Math.pow(1 + rate, periods);
  }

  /**
   * Calculate internal rate of return (IRR) using Newton-Raphson method
   */
  /**
   * Calculate internal rate of return (IRR) using Newton-Raphson method.
   * @param cashFlows Array of cash flows (numbers)
   * @param guess Initial guess for IRR (default 0.1)
   * @returns Calculated IRR as a number
   */
  static calculateIRR(cashFlows: number[], guess: number = 0.1): number {
    let irr: number = guess;
    for (let i = 0; i < 1000; i++) {
      let npv: number = 0;
      let d_npv: number = 0;
      for (let t = 0; t < cashFlows.length; t++) {
        npv += cashFlows[t] / Math.pow(1 + irr, t);
        d_npv -= t * cashFlows[t] / Math.pow(1 + irr, t + 1);
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
